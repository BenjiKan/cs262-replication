SERVER_PORTS = [50054, 50055, 50056]
N_SERVER_PORTS = len(SERVER_PORTS)
INTERNAL_PORTS = [9700, 9701, 9702]

if __name__ == "__main__":
    print(f"All available constants: {dict(filter(lambda k: k[0][0] != '_', globals().items()))}")