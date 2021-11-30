import asyncio
from threading import Thread


class Transport:
    def __init__(self, component):
        self.info = {"name": "skeleton",
                     "author": "Und3rf10w",
                     "desc": "Skeleton for building out transports",
                     "version": "0.01-dev"
                     }
        # Should always be initialized here
        self.config = {}
        # You REALLY SHOULD keep this in, so you can use the same logging engine
        self.logging = None
        self.component = component
        self.implant_id = None
        self.transport_id = None
        self.transport_dir = None
        self.async_loop = None

    def start_background_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def prep_transport(self, transport_config):
        # Here you take the transport configuration and make a configuration that you're going to use by populating
        #   self.config
        self.config = transport_config
        # You REALLY SHOULD keep this in, so you can use the same logging engine
        self.logging = transport_config['logging']
        self.transport_id = self.config['transport_id']

        self.transport_dir = self.config['transport_dir']

        self.async_loop = asyncio.new_event_loop()
        t = Thread(target=self.start_background_loop, args=(self.async_loop,), daemon=False)
        self.async_loop.create_task(asyncio.run_coroutine_threadsafe(self.async_read))
        t = t.start()
        self.logging.log(f"Transport prepared", level="debug", source=self.info['name'])

    async def async_send(self, data):
        with open(self.transport_dir + "test.txt", "wb+") as f:
            f.write(data)

    async def async_read(self):
        with open(self.transport_dir + "test.txt", "rb+") as f:
            data = f.read()
            f.seek(0)
            f.write()
        return data

    def send_data(self, data):
        asyncio.create_task(self.async_send(data))

    def recv_data(self):
        data = asyncio.create_task(self.async_read())
        return data
