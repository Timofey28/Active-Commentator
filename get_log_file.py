import pysftp
from config import settings


if __name__ == '__main__':
    try:
        with pysftp.Connection(
                host=settings.hostname,
                username=settings.username,
                private_key=settings.private_key_path
        ) as sftp:
            print("Connection succesfully established ...")
            sftp.get('/root/Active-Commentator/info.log', 'info.log')
    except Exception as e:
        print(e)
    else:
        print("*** Файл на базе! ***")