
import torch

def check_cuda():
    print("=== CUDA Diagnostic ===")
    print(f"PyTorch Version: {torch.__version__}")
    
    cuda_available = torch.cuda.is_available()
    print(f"CUDA Available: {cuda_available}")
    
    if cuda_available:
        print(f"CUDA Version: {torch.version.cuda}")
        print(f"Device Name: {torch.cuda.get_device_name(0)}")
        print(f"Device Count: {torch.cuda.device_count()}")
        print("\nSUCCESS: Your system is ready for GPU acceleration!")
    else:
        print("\n[!] CUDA is NOT available to PyTorch.")
        print("Possible reasons:")
        print("1. NVIDIA Drivers are not installed or outdated.")
        print("2. CUDA Toolkit is not installed (Version 12.1 recommended).")
        print("3. PyTorch was installed without CUDA support.")
        print("\nAction: Follow the guide in walkthrough.md to fix this.")

if __name__ == "__main__":
    check_cuda()
