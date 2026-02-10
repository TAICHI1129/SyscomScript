def run_main(py_code: str):
    namespace = {}
    exec(py_code, namespace)

    if "Main" not in namespace:
        raise RuntimeError("Main class not found")

    main = namespace["Main"]()

    if not hasattr(main, "run"):
        raise RuntimeError("run() not found in Main class")

    main.run()
