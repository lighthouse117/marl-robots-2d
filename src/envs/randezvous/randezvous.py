import random
import time
import os
import numpy as np
import pygame
import datetime
from typing import List, Tuple
from envs.diamond.utils import one_hot_encode

from envs.randezvous.world import RandezvousWorld
from envs.randezvous.agents import Direction


class RandezvousEnv:
    """
    マルチエージェント2Dシミュレーション環境(エージェント数: 2)
    """

    OFFSET = 40
    INFO_HEIGHT = 270
    INFO_MARGIN = 40
    SA_INFO_WIDTH = 400
    SA_INFO_MARGIN = 25

    BG_COLOR = (10, 16, 21)
    INFO_BG_COLOR = (30, 33, 36)
    INFO_TEXT_COLOR = (220, 220, 220)
    INFO_TEXT_COLOR2 = (145, 150, 155)

    FPS = 60

    FONT_NAME = "Arial"

    def __init__(
        self,
        episode_limit: int,
        agent_velocity: float,
        guard_velocity: float,
        channel_size: int,
        lidar_angle: float,
        lidar_interval: float,
        reward_success: float,
        reward_failure: float,
        seed=None,
        debug: bool = False,
        enable_render: bool = False,
        test_mode: bool = False,
    ):
        # os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.init()
        pygame.display.set_caption("Randezvous Env")
        np.set_printoptions(precision=2, suppress=True)

        self.episode_limit = episode_limit
        self.debug = debug
        self.reward_success = reward_success
        self.reward_failure = reward_failure
        self.agent_velocity = agent_velocity
        self.guard_velocity = guard_velocity
        self.channel_size = channel_size
        self.lidar_angle = lidar_angle
        self.lidar_interval = lidar_interval
        self.enable_render = enable_render

        self.world = RandezvousWorld(
            self.agent_velocity,
            self.guard_velocity,
            self.channel_size,
            self.lidar_angle,
            self.lidar_interval,
        )
        self.n_agents = len(self.world.agents)

        self.n_lasers = self.world.get_num_lasers()

        self.window = None
        self.WINDOW_WIDTH = self.world.WIDTH + self.SA_INFO_WIDTH + 2 * self.OFFSET
        self.WINDOW_HEIGHT = self.world.HEIGHT + self.INFO_HEIGHT + self.OFFSET
        self.map_screen = pygame.Surface((self.world.WIDTH, self.world.HEIGHT))
        self.info_screen = pygame.Surface((self.WINDOW_WIDTH, self.INFO_HEIGHT))
        self.sa_screen = pygame.Surface((self.SA_INFO_WIDTH, self.world.HEIGHT))
        self.clock = pygame.time.Clock()

        self._episode_count = 0
        self._episode_steps = 0
        self._total_steps = 0

        self.goal_reached = False
        self.failed = False

        self.success_count = 0
        self.timeout_count = 0

        self.goal_distance = 0
        self.laser_distances = []

        self.now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        self.font1 = pygame.font.SysFont(self.FONT_NAME, 45)
        self.font2 = pygame.font.SysFont(self.FONT_NAME, 30)
        self.font3 = pygame.font.SysFont(self.FONT_NAME, 24)
        self.font4 = pygame.font.SysFont(self.FONT_NAME, 20)
        self.font5 = pygame.font.SysFont(self.FONT_NAME, 16)
        self.font6 = pygame.font.SysFont(self.FONT_NAME, 14)

        self.test_mode = test_mode

    def get_env_info(self) -> dict:
        """
        環境の情報を取得する
        """
        return {
            "state_shape": self.get_state_size(),
            "obs_shape": self.get_obs_size(),
            "n_actions": self.get_total_actions(),
            "n_agents": self.n_agents,
            "episode_limit": self.episode_limit,
        }

    def get_obs_size(self):
        """
        エージェントの部分観測のサイズを返す
        """
        # サイズは全エージェントで統一する
        # RA座標 + 警備員座標 +　レーザー +  ゴール相対座標 + メッセージ
        # エージェントによって無効な部分は0で埋める
        self.obs_size = 2 + self.n_lasers

        # self.obs_size = 2 + 2 + self.n_lasers + 2 + self.channel_size
        return self.obs_size

    def get_state_size(self):
        """
        グローバル状態のサイズを返す
        """
        return 4

    def get_total_actions(self):
        """
        エージェントがとることのできる行動の数を返す
        """
        # サイズは全エージェントで統一する
        # エージェントによって無効な部分がある

        # 前、後、左、右に動く
        self.n_actions = 4
        return self.n_actions

    def step(self, actions: List[int]) -> Tuple[float, bool, dict]:
        """
        行動を実行して、環境を1ステップ進める

        戻り値:
            - reward: 報酬
            - terminated: エピソード完了フラグ
            - info: その他の情報
        """

        assert len(actions) == self.n_agents, "Invalid action size"

        self.terminated = False
        info = {
            "is_success": False,
            "timeout": False,
        }

        # 警備員の移動
        self.world.step()

        # エージェントの行動を実行
        for agent, action in zip(self.world.agents, actions):
            # 動く
            if action == 0:
                agent.move(Direction.LEFT)
            elif action == 1:
                agent.move(Direction.RIGHT)
            elif action == 2:
                agent.move(Direction.UP)
            elif action == 3:
                agent.move(Direction.DOWN)

        # タイムステップを進める

        if not self.test_mode:
            self._total_steps += 1

        self._episode_steps += 1

        # 終了判定
        if self.world.check_collision():
            # 衝突したら終了
            self.terminated = True
            info["is_success"] = False
            self.failed = True
        elif self.world.check_both_goal():
            # ゴールしたら終了
            self.terminated = True
            info["is_success"] = True
            self.goal_reached = True
            self.success_count += 1
        elif self._episode_steps >= self.episode_limit:
            # ステップ数が上限に達したら終了
            self.terminated = True
            info["is_success"] = False
            info["timeout"] = True
            self.timeout = True
            self.timeout_count += 1

        # 報酬を獲得
        self.reward = self.get_reward()

        # 総走行距離
        if self.terminated:
            # info["mileage"] = self.world.get_mileage()

            if self.test_mode:
                self.render()
                # 画像を保存
                pygame.image.save(
                    self.window, f"images/{self.now_str}_{self._episode_count}.png"
                )

        # 描画
        if self.test_mode:
            self.render()

        return self.reward, self.terminated, info

    def reset(self, episode, test_mode=False, print_log=False):
        """
        環境をリセットする

        戻り値:
            - observations: 観測値
            - states: グローバル状態
        """
        self.world.reset(random_direction=True)

        self._episode_steps = 0
        self._episode_count += 1
        self.goal_reached = False
        self.failed = False
        self.goal_distance = 0
        self.laser_distances = []
        self.test_mode = test_mode
        self.timeout = False

        return self.get_obs(), self.get_state()

    def get_reward(self) -> float:
        """
        報酬関数
        """
        # ゴールまでの正規化された距離
        self.goal_distance = self.world.get_sum_distance_from_goal()

        if self.goal_reached:
            # ゴールに到達
            print("Goal reached!")
            return self.reward_success
        elif self.failed:
            # 衝突
            return self.reward_failure - self.goal_distance
        # elif self.timeout:
        #     # タイムアウト
        #     return self.reward_failure - self.goal_distance
        else:
            # 毎ステップ、ゴールまでの距離をペナルティとして与える
            return -1 * self.goal_distance

    def get_obs(self) -> List[float]:
        """
        全てのエージェントの観測値を取得する
        NOTE: 分散実行時はエージェントは自分自身の観測のみ用いるようにする
        """

        # RA座標 + 警備員座標 +　レーザー +  ゴール相対座標 + メッセージ

        obs = []

        for agent in self.world.agents:
            obs.append(self.world.get_goal_relative_position(agent))

        self.obs = np.array(obs)

        return self.obs

        # RAの絶対座標
        agent_absolute_position = self.world.get_normalized_agent_position()

        # 警備員の絶対座標
        guard_absolute_position = self.world.get_normalized_guard_position()

        # RAからみたゴールの相対的な座標
        relative_goal_position = self.world.get_relative_normalized_goal_position()

        # LiDARセンサー値 [d1, ..., dn]
        laser_distances = self.world.laser_scan()

        # 通信チャンネル
        one_hot_message = one_hot_encode(self.world.get_message(), self.channel_size)

        self.obs = np.concatenate(
            (
                relative_goal_position,
                laser_distances,
            )
        )

        # self.obs = np.concatenate(
        #                 (
        #                     agent_absolute_position,
        #                     guard_absolute_position,
        #                     relative_goal_position,
        #                     laser_distances,
        #                     one_hot_message,
        #                 )
        #             )

        return self.obs

        for agent in self.world.agents():
            # 観測できない所は0で埋める
            if agent.movable:
                # RA
                obs.append(
                    np.concatenate(
                        (
                            np.zeros(2),
                            np.zeros(2),
                            relative_goal_position,
                            laser_distances,
                            one_hot_message,
                        )
                    )
                )

            if agent.sendable:
                # RA
                obs.append(
                    np.concatenate(
                        (
                            np.zeros(2),
                            np.zeros(2),
                            np.zeros(2),
                            np.zeros(self.n_lasers),
                            np.zeros(self.channel_size),
                        )
                    )
                )
                # SA
                # obs.append(
                #     np.concatenate(
                #         (
                #             agent_absolute_position,
                #             guard_absolute_position,
                #             relative_goal_position,
                #             np.zeros(self.n_lasers),
                #             np.zeros(self.channel_size),
                #         )
                #     )
                # )
        self.obs = obs
        return np.array(obs)

    def get_state(self):
        """
        グローバル状態を取得する
        NOTE: この関数は分散実行時は用いないこと
        """

        state = []

        for agent in self.world.agents:
            state.append(self.world.get_agent_position(agent))

        self.state = np.array(state).flatten()
        return self.state

        # RAの絶対座標
        agent_absolute_position = self.world.get_normalized_agent_position()
        # 警備員の絶対座標
        guard_absolute_position = self.world.get_normalized_guard_position()
        # RAからみたゴールの相対的な座標
        relative_goal_position = self.world.get_relative_normalized_goal_position()
        # LiDARセンサー値 [d1, ..., dn]
        laser_distances = self.world.laser_scan()
        # 通信チャンネル
        one_hot_message = one_hot_encode(self.world.get_message(), self.channel_size)

        return np.concatenate(
            (
                relative_goal_position,
                laser_distances,
            )
        ).astype(np.float32)

        return np.concatenate(
            (
                agent_absolute_position,
                guard_absolute_position,
                relative_goal_position,
                laser_distances,
                one_hot_message,
            )
        ).astype(np.float32)

    def get_avail_actions(self):
        """
        全エージェントの選択可能な行動のマスクを返す
        """
        avail_actions = []
        # エージェントごと
        for agent in self.world.agents:
            # マスクを作成
            avail_mask = [1] * self.n_actions
            avail_actions.append(avail_mask)

        # print(avail_actions)
        return np.array(avail_actions)

    def render(self, mode="human"):
        """
        環境を描画する
        """
        self.clock.tick(self.FPS)
        if self.window is None:
            self.window = pygame.display.set_mode(
                (self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
            )
        self.__draw()
        pygame.event.pump()
        pygame.display.flip()

        if self.terminated:
            time.sleep(0.5)
        # elif self.render_mode == "rgb_array":
        #     return pygame.surfarray.array3d(self.screen)

    def __draw(self):
        """
        Pygameの描画処理
        """
        self.window.fill(self.BG_COLOR)
        self.map_screen.fill(self.BG_COLOR)
        self.info_screen.fill(self.BG_COLOR)
        self.sa_screen.fill((self.BG_COLOR))

        self.world.draw(self.map_screen)
        self.__draw_info()

        self.window.blit(self.map_screen, (self.OFFSET, self.INFO_HEIGHT))
        self.window.blit(self.info_screen, (0, 0))
        self.window.blit(
            self.sa_screen, (self.OFFSET + self.world.WIDTH, self.INFO_HEIGHT)
        )

    def __draw_info(self):
        episode_text = self.font2.render(
            f"Episode: {self._episode_count} ({self._total_steps})",
            True,
            self.INFO_TEXT_COLOR,
        )
        timestep_text = self.font3.render(
            f"Timestep: {self._episode_steps}", True, self.INFO_TEXT_COLOR2
        )
        distance_text = self.font3.render(
            f"Distance from goal: {self.goal_distance:.3f}",
            True,
            self.INFO_TEXT_COLOR2,
        )
        ra_obs_text = self.font4.render(
            f"RA Obs: {self.obs[0]}",
            True,
            self.INFO_TEXT_COLOR2,
        )
        # sa_obs_text = self.font4.render(
        #     f"RA Obs: {self.obs[1]}",
        #     True,
        #     self.INFO_TEXT_COLOR2,
        # )
        reward_text = self.font3.render(
            f"Reward: {self.reward: .2f}",
            True,
            self.INFO_TEXT_COLOR2,
        )
        pygame.draw.rect(
            self.info_screen,
            self.INFO_BG_COLOR,
            (
                self.INFO_MARGIN,
                self.INFO_MARGIN,
                self.WINDOW_WIDTH - 2 * self.INFO_MARGIN,
                self.INFO_HEIGHT - 2 * self.INFO_MARGIN,
            ),
            0,
            20,
        )
        self.info_screen.blit(
            episode_text, (self.INFO_MARGIN + 24, self.INFO_MARGIN + 20)
        )
        self.info_screen.blit(
            timestep_text, (self.INFO_MARGIN + 24, self.INFO_MARGIN + 65)
        )
        self.info_screen.blit(
            distance_text, (self.INFO_MARGIN + 24, self.INFO_MARGIN + 95)
        )
        self.info_screen.blit(
            reward_text, (self.INFO_MARGIN + 24, self.INFO_MARGIN + 140)
        )

        pygame.draw.rect(
            self.sa_screen,
            self.INFO_BG_COLOR,
            (
                self.SA_INFO_MARGIN,
                0,
                self.SA_INFO_WIDTH - 2 * self.SA_INFO_MARGIN,
                self.world.HEIGHT,
            ),
            0,
            15,
        )
        sa_title = self.font3.render(
            "Sensor Agent",
            True,
            self.INFO_TEXT_COLOR,
        )
        sa_message_title = self.font4.render(
            "Send Message:",
            True,
            self.INFO_TEXT_COLOR2,
        )
        sa_message_value = self.font2.render(
            str(self.world.channel),
            True,
            self.INFO_TEXT_COLOR,
        )
        # self.sa_screen.blit(sa_title, (self.SA_INFO_MARGIN + 15, 20))
        # self.sa_screen.blit(sa_message_title, (self.SA_INFO_MARGIN + 15, 60))
        # self.sa_screen.blit(sa_message_value, (self.SA_INFO_MARGIN + 100, 100))

        if self.failed:
            result_text = self.font1.render("FAILED", True, (160, 50, 50))
            self.info_screen.blit(
                result_text, (self.WINDOW_WIDTH - 300, self.INFO_MARGIN + 50)
            )
        elif self.goal_reached:
            result_text = self.font1.render("CLEAR !!!!!!", True, (50, 160, 80))
            self.info_screen.blit(
                result_text, (self.WINDOW_WIDTH - 300, self.INFO_MARGIN + 50)
            )

    def close(self):
        """
        環境を閉じる
        """
        pygame.quit()
