import os
import sys

# ✅ Caminho absoluto para o projeto
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from dao.mongo.v1.evolution_dao import EvolutionInstanceDAO


def fetch_all_instances(uid: str, verbose: bool = False):
    instances = EvolutionInstanceDAO.list_all_instances(uid)

    if verbose:
        print(f"\n🔎 Usuário: {uid}")
        if not instances:
            print("⚠️ Nenhuma instância encontrada!")
        else:
            print(f"✅ {len(instances)} instâncias:")
            for inst in instances:
                print(f" - {inst.get('_id')} | Nome: {inst.get('metadata', {}).get('instance_name')}")

    return instances


def fetch_instance_by_name(instance_name: str, verbose: bool = False):
    collection = EvolutionInstanceDAO._get_collection()
    docs = collection.find({})  # Varre todos os usuários

    for doc in docs:
        uid = doc["user_id"]
        inst, telefone = EvolutionInstanceDAO.get_instance_by_name(uid, instance_name)  # precisa retornar também telefone
        if inst:
            if verbose:
                print(f"\n🎯 Instância encontrada no usuário {uid}:")
                print(inst)
            return uid, telefone, inst

    if verbose:
        print(f"❌ Nenhuma instância com o nome '{instance_name}' encontrada!")

    return None, None, None


def main():
    print("\n======= TESTE DE INSTÂNCIAS =======")
    print("1 - Listar todas instâncias de um usuário")
    print("2 - Buscar instância por nome")
    opcao = input("Digite 1 ou 2: ")

    if opcao == "1":
        uid = input("Digite o UID do usuário: ")
        fetch_all_instances(uid, verbose=True)

    elif opcao == "2":
        name = input("Digite o nome da instância: ")
        fetch_instance_by_name(name, verbose=True)

    else:
        print("❌ Opção inválida!")


if __name__ == "__main__":
    main()
