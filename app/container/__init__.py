from app.container.ai import AIContainer
from app.container.infra import InfraContainer


class AppContainer:
    """应用级 IoC 容器，只管理全局共享的长生命周期单例。

    短生命周期对象（ChatService 等）由 ServiceFactory 按请求创建，
    不从 Container 直接获取。
    """

    def __init__(self) -> None:
        self.ai = AIContainer()
        self.infra = InfraContainer()


_container: AppContainer | None = None


def init_container() -> AppContainer:
    """在 create_app() 中调用，初始化全局单例容器。"""
    global _container
    _container = AppContainer()
    return _container


def get_container() -> AppContainer:
    """获取已初始化的容器实例。"""
    if _container is None:
        raise RuntimeError("Container not initialized. Call init_container() first.")
    return _container


__all__ = ["AppContainer", "init_container", "get_container"]
