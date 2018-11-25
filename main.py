import worker

if __name__ == "__main__":
    worker = worker.Worker("2018-10-30T00:00:00", "2018-10-30T00:59:59")
    worker.run()