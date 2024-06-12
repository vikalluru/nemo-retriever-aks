# Deploying NeMo Microservices (NVSTACK) on Azure Kubernetes service

This guide provides step-by-step instructions on how to set up and deploy Nvidia Inference Microservices (NIMs) and NeMo microservices on Azure. Follow the instructions below to get started.

## Setup your Azure Account
To begin, log in to your Azure account and set the appropriate subscription.

```bash
az login
az account set --subscription <your subscription>
```

## Create AKS Node Pool
Create a new node pool in your Azure Kubernetes Service (AKS) cluster. This node pool will host the GPU nodes required for running Nvidia microservices.

```bash
az aks nodepool add --resource-group <your resource group name> --cluster-name <your aks cluster name> --name <nodepool name> --node-count 2 --skip-gpu-driver-install --node-vm-size Standard_NC48ads_A100_v4 --node-osdisk-size 256 --max-pods 110
```

## Get Your AKS Context
Retrieve the AKS context to interact with your AKS cluster.

```bash
az aks get-credentials --resource-group <your resource group name> --name <your aks name>
```

## Deploy NIM General Availability (GA) on AKS
Add the Nvidia Helm repository and deploy the GPU operator to manage GPU resources.

```bash
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia --pass-credentials
helm repo update
helm install --create-namespace --namespace nvidia-gpu-operator nvidia/gpu-operator --wait --generate-name
```

Clone the NIM deployment Helm charts and configure secrets.

```bash
git clone https://github.com/NVIDIA/nim-deploy/helm
cd nim-deploy/helm
export NGC_CLI_API_KEY="key from ngc"
kubectl create namespace inference-ms
kubectl create --namespace inference-ms secret docker-registry registry-secret --docker-server=nvcr.io --docker-username='$oauthtoken' --docker-password=$NGC_CLI_API_KEY
kubectl create --namespace inference-ms secret generic ngc-api --from-literal=NGC_CLI_API_KEY=$NGC_CLI_API_KEY
```

Deploy NIM on your AKS cluster using Helm.

```bash
helm --namespace inference-ms install my-nim nim-llm/ -f ./nim-llama3-8b-values.yaml
```

## Deploy Embedding Microservice on AKS
Deploy the embedding microservice using Helm.

```bash
helm --namespace inference-ms install nemo-embedding embedding-ms
```

## Deploy Reranking Microservice on AKS
Deploy the reranking microservice using Helm.

```bash
helm --namespace inference-ms install nemo-reranking reranking-ms
```

## Scale Down Your Node Pool to Save Costs
To save costs, scale down your GPU node pool when not in use.

```bash
az aks nodepool scale \
  --resource-group <your resource group name> \
  --cluster-name <your aks cluster name> \
  --name <nodepool name> \
  --node-count 0
```

## Check if Your Nodes are Down
Verify the status of your node pool to ensure it has scaled down correctly.

```bash
az aks nodepool show \
  --resource-group <your resource group name> \
  --cluster-name <your aks cluster name> \
  --name <nodepool name>
```

## Respin Your Nodes Next Time
When you need to use the GPU nodes again, scale the node pool back up.

```bash
az aks nodepool scale \
  --resource-group <your resource group name> \
  --cluster-name <your aks cluster name> \
  --name <nodepool name> \
  --node-count 2
```

Follow these instructions to efficiently manage your Nvidia Inference Microservices and NeMo microservices on Azure, ensuring optimal performance and cost-efficiency.
```
