import logging
import signal
import time
import docker
import uuid

from .ping import ping

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ServerInstanceHandler:
    def signal_handler(self, sig, frame):
        self.stop()

    def wait(self, timeout: int = 120):
        """Timeout is in seconds"""

        logging.info(f"Waiting for server to be up ...")

        for n in range(timeout):
            logging.debug(f"Trying to ping localhost:{self.port}")

            try:
                latency = ping("localhost", self.port)
                logging.info(f"Success ping in {latency} after {n}s")
                return latency
            except:
                logging.debug(f"Failed status ping {n}")

            time.sleep(1)

        logging.info(f"Couldn't ping the server")
        # self.stop()

    def stop(self):
        raise NotImplementedError


class DockerInstance(ServerInstanceHandler):
    def __init__(
        self,
        port: int = 25565,
        rcon_port: int = 25575,
        container_name: str = uuid.uuid4(),
        wait: bool = True,
        image: str = "ghcr.io/portalhubyt/template_server:latest",
        eula: bool = False,
        version: str = "latest",
    ):

        if eula == False:
            exit(
                "Please accept the EULA before running the server by providing 'eula=True' as an argument to create()"
            )

        signal.signal(signal.SIGINT, self.signal_handler)
        self.name = container_name
        self.port = port
        self.rcon_port = rcon_port
        self.eula = eula
        self.version = version
        self.client = docker.APIClient()
        self.client.pull(image)

        try:
            self.container = self.client.create_container(
                image,
                ports=[25565, 25575],
                host_config=self.client.create_host_config(
                    port_bindings={25565: port, 25575: self.rcon_port}
                ),
                environment=[f"EULA={self.eula}", f"VERSION={self.version}"],
                name=container_name,
            )

            self.client.start(self.container)

            print("container")
        except Exception as e:
            raise e
        if wait == True:
            self.wait()

    def stop(self):

        logging.info(f"Stopping ...")
        self.client.stop(self.container)
        self.client.wait(self.container)
        self.client.remove_container(self.container)
        logging.info(f"Removed container")
