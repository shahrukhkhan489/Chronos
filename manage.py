from chronos import create_app

app = create_app()
if __name__ == '__main__':
    from chronos import model
    model.manage()


def run():
    app.run()
