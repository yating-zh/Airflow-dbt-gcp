#FROM astrocrpublic.azurecr.io/runtime:3.3-11
FROM quay.io/astronomer/astro-runtime:12.7.1 
#这行指定了基础的image，这个image已经包含了Airflow和一些常用的dependencies。我们在这个基础上安装dbt和其他需要的Python包。

# Set environment variables
ENV VENV_PATH="/usr/local/airflow/dbt_venv" 
# 指定了虚拟环境的安装位置。我们将dbt和其他Python包安装在这个虚拟环境中，以避免与系统Python环境冲突。
ENV PATH="$VENV_PATH/bin:$PATH" 
# 这行将虚拟环境的bin目录添加到PATH中，这样我们就可以直接使用dbt命令，而不需要指定完整路径。

# Install dbt into a virtual environment and upgrade pip + setuptools
RUN python -m venv $VENV_PATH && \
    source $VENV_PATH/bin/activate && \
    pip install --upgrade pip setuptools && \
    pip install --no-cache-dir dbt-bigquery==1.9.2 pandas Faker pyarrow numpy && \
    deactivate


# Store environment activation script inside Airflow home
RUN echo "source $VENV_PATH/bin/activate" > /usr/local/airflow/dbt_env.sh
RUN chmod +x /usr/local/airflow/dbt_env.sh
# the above line is to make the script executable. This script can be sourced in Airflow tasks to activate the virtual environment before running dbt commands.
# chmod is a command to change the file mode (permissions) of a file. +x means adding execute permission for the user, group, and others.


# FROM quay.io/astronomer/astro-runtime:12.7.1

# # Set environment variables
# ENV VENV_PATH="/usr/local/airflow/dbt_venv"
# ENV PATH="$VENV_PATH/bin:$PATH"

# # Copy requirements.txt into the image
# COPY requirements.txt /usr/local/airflow/requirements.txt

# # Create virtual environment and install dependencies
# RUN python -m venv $VENV_PATH \
#     && $VENV_PATH/bin/pip install --upgrade pip setuptools \
#     && $VENV_PATH/bin/pip install --no-cache-dir dbt-bigquery==1.5.3 pandas Faker pyarrow numpy \
#     && $VENV_PATH/bin/pip install --no-cache-dir -r /usr/local/airflow/requirements.txt

# # Store environment activation script inside Airflow home
# RUN echo "source $VENV_PATH/bin/activate" > /usr/local/airflow/dbt_env.sh \
#     && chmod +x /usr/local/airflow/dbt_env.sh