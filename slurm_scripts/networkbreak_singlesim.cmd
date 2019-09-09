#!/bin/bash
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 20
#SBATCH --time=5:59:00
#SBATCH --mail-type=begin
#SBATCH --mail-type=end
#SBATCH --mail-user=ctokita@princeton.edu

module load anaconda3
cd InformationCascades/
srun python3 scripts/2_parallel-networkbreaking.py -1
