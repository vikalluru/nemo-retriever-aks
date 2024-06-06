az login
az account set --subscription <your subscription>
az aks get-credentials --resource-group <your resource group name> --name <your aks name>

az aks nodepool add --resource-group <your resource group name> --cluster-name <your aks cluster name> --name <nodepool name> --node-count 2 --skip-gpu-driver-install --node-vm-size Standard_NC48ads_A100_v4 --node-osdisk-size 256 --max-pods 110

helm repo add nvidia https://helm.ngc.nvidia.com/nvidia --pass-credentials
helm repo update
helm install --create-namespace --namespace nvidia-gpu-operator nvidia/gpu-operator --wait --generate-name

git clone https://github.com/NVIDIA/nim-deploy/helm
cd nim-deploy/helm
export NGC_CLI_API_KEY="key from ngc"
kubectl create namespace inference-ms
kubectl create --namespace inference-ms secret docker-registry registry-secret --docker-server=nvcr.io --docker-username='$oauthtoken' --docker-password=$NGC_CLI_API_KEY
kubectl create --namespace inference-ms secret generic ngc-api --from-literal=NGC_CLI_API_KEY=$NGC_CLI_API_KEY

helm --namespace inference-ms install my-nim nim-llm/ -f ./nim-llamam3-XXX-values.yaml

helm --namespace inference-ms install vllm vllm -f path/to/your/custom-values.yaml

helm --namespace inference-ms install nemo-embedding embedding-ms