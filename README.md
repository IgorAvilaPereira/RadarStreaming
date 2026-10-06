# Radar de Streaming — Android

O app foi configurado para gerar um APK instalável em `dist/android/radar-de-streaming.apk`.

## Gerar o APK no Linux Mint

O projeto requer Python 3.12 ou superior. No terminal, na pasta do projeto:

1. Instale as ferramentas básicas do sistema:

   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv python3-pip
   ```

2. Confira a versão do Python:

   ```bash
   python3 --version
   ```

   Se for inferior a 3.12, instale uma versão compatível com a versão/base Ubuntu do seu Linux Mint antes de continuar.

3. Crie e ative um ambiente virtual e instale a CLI do Flet:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install flet-cli
   ```

4. Gere e copie o APK para o diretório de entrega:

   ```bash
   bash scripts/build_android.sh
   ```

Na primeira compilação, o Flet pode baixar/configurar Flutter, Java e Android SDK automaticamente; é necessário ter internet e espaço livre em disco. O script executa `flet build apk --yes -v`, procura o APK produzido em `build/apk/` e o copia para `dist/android/radar-de-streaming.apk`. Execute novamente o mesmo comando para gerar uma versão atualizada; o arquivo de entrega será substituído.

O APK gerado localmente não está incluído neste projeto até que o script seja executado em uma máquina com as ferramentas Android configuradas. Consulte também a documentação oficial para opções de assinatura e publicação: <https://flet.dev/docs/publish>.
