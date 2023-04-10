SERVER_PORTS = [50054, 50055, 50056]
N_SERVER_PORTS = len(SERVER_PORTS)

if __name__ == "__main__":
    print(f"All available constants: {dict(filter(lambda k: k[0][0] != '_', globals().items()))}")