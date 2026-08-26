# Domain Monitoring Platform - AWS IaC and CI/CD

An end-to-end DevOps implementation that provisions a complete AWS environment,
configures Jenkins and its agents automatically, validates a containerized Flask
application with Selenium, publishes immutable images, and deploys them to a
load-balanced production environment.

## Project Goal

The project replaces a manually configured delivery process with a repeatable,
version-controlled platform:

- Infrastructure is created on demand with Terraform.
- Operating systems and services are configured with Ansible.
- Jenkins is configured as code instead of through manual UI setup.
- Every deployment uses the exact image that passed automated tests.
- Production runs on two EC2 instances behind an Application Load Balancer.

## Architecture

~~~mermaid
flowchart LR
    Dev[Developer] --> GitHub[GitHub]
    GitHub --> Jenkins[Jenkins Controller]
    Jenkins --> DockerAgent[Docker Agent]
    DockerAgent --> Build[Build Backend and Frontend]
    Build --> Selenium[Headless Selenium Tests]
    Selenium --> Hub[Docker Hub]
    Jenkins --> AnsibleAgent[Ansible Agent]
    AnsibleAgent --> Prod1[Production EC2 1]
    AnsibleAgent --> Prod2[Production EC2 2]
    Hub --> Prod1
    Hub --> Prod2
    User[User] --> ALB[Application Load Balancer]
    ALB --> Prod1
    ALB --> Prod2
~~~

### AWS Compute Roles

| Instance | Responsibility |
|---|---|
| Jenkins controller | Runs Jenkins in Docker and loads JCasC configuration |
| Docker agent | Builds images and runs the isolated CI test environment |
| Ansible agent | Executes production deployment playbooks |
| Production 1 | Runs the frontend and backend containers |
| Production 2 | Runs the frontend and backend containers |

## Technology Stack

- AWS EC2, Application Load Balancer, Target Groups, Security Groups
- Terraform
- Ansible and dynamic AWS inventory
- Jenkins Pipeline and Jenkins Configuration as Code
- Docker and Docker Hub
- Python and Flask
- Selenium, Chromium, and Pytest
- Linux systemd services
- Git and GitHub

## Delivery Pipeline

Jenkins/Jenkinsfile.iac-cicd performs:

1. Checks out the repository on the Docker agent.
2. Reads the short Git commit ID.
3. Builds separate backend and frontend images.
4. Tags both images with the commit ID for traceability.
5. Starts an isolated environment on a temporary Docker network.
6. Waits for the backend and frontend health endpoints.
7. Builds and runs containerized headless Selenium tests.
8. Pushes the tested images to Docker Hub.
9. Switches execution to the Ansible agent.
10. Deploys the exact tested tags to both production instances.
11. Verifies health and cleans temporary CI resources.

Image tags are immutable and traceable to source:

    oranamar2003/domain-monitoring-system:backend-<commit-id>
    oranamar2003/domain-monitoring-system:frontend-<commit-id>

## Infrastructure as Code

Terraform provisions:

- Five EC2 instances.
- Dedicated security groups for Jenkins, agents, production, and the ALB.
- An Application Load Balancer.
- A target group with two production targets.
- An HTTP listener and health-check configuration.

The implementation uses the default AWS VPC and an existing EC2 key pair to
keep the project focused on CI/CD automation. Environment-specific values are
supplied through an ignored terraform.tfvars file. No credentials are stored in
the repository.

## Configuration Management

Ansible discovers EC2 instances dynamically from AWS tags and assigns them to
the Jenkins controller, Docker agent, Ansible agent, and production groups.

The roles:

- Install common system dependencies.
- Install, enable, and start Docker.
- Build and run the Jenkins controller container.
- Load Jenkins configuration through JCasC.
- Register both Jenkins agents automatically.
- Run each agent JAR as a managed systemd service.
- Use Java 21 for Jenkins Remoting compatibility.
- Provide persistent agent work and temp directories.
- Install Ansible on the deployment agent.
- Pull and deploy versioned images on production.

The Ansible agent connects to production over private VPC addresses. Security
group references allow SSH from the agent to production without exposing that
deployment path to the public internet.

## Security Practices

- Docker Hub authentication uses a personal access token stored in Jenkins.
- AWS access keys are stored in Jenkins Credentials.
- The production SSH key is stored as an SSH credential.
- The Flask secret is stored as secret text.
- Pipeline output masks supported secret values.
- Credentials, local Terraform variables, state files, and private keys are
  excluded from Git.
- Security group rules follow role-based access rather than one shared group.

| Jenkins Credential ID | Purpose |
|---|---|
| docker-hub | Publish tested container images |
| aws-credentials | Discover AWS instances dynamically |
| production-ssh-key | Connect Ansible to production |
| dms-secret-key | Supply the Flask application secret |

## Verified Result

The complete workflow has been validated successfully:

- Backend and frontend images built successfully.
- All 8 headless Selenium tests passed.
- Commit-tagged images were published to Docker Hub.
- Both production deployments completed with zero failed or unreachable hosts.
- Both ALB targets reported Healthy.
- Registration, login, domain management, and scanning worked through the ALB.
- Temporary CI containers, networks, and images were cleaned automatically.

## Repository Structure

    Jenkins/
      Jenkinsfile.iac-cicd

    infra/cicd/
      terraform/
        instances.tf
        security-groups.tf
        load-balancer.tf
        variables.tf
        outputs.tf

      ansible/
        inventory_aws_ec2.yml
        site.yml
        deploy-production.yml
        group_vars/
        roles/

## Running the Platform

### Provision Infrastructure

    cd infra/cicd/terraform
    terraform init
    terraform validate
    terraform plan
    terraform apply

### Configure the Environment

    cd infra/cicd/ansible
    export ANSIBLE_CONFIG="$PWD/ansible.cfg"
    ansible-playbook site.yml

Jenkins credentials are then added manually. The generated Pipeline job can
execute the complete build, test, publish, and deployment flow.

## Engineering Decisions and Tradeoffs

### Separate Build and Deployment Agents

Docker workloads and deployment credentials are isolated on different Jenkins
agents. This reduces coupling and demonstrates label-based workload placement.

### Commit-Based Image Tags

Production receives the exact artifacts that passed Selenium. A deployment can
be traced to a Git commit, and rollback can target an earlier known image.

### Dynamic Inventory

Ansible uses AWS tags instead of hard-coded IP addresses. Recreated instances
are discovered automatically.

### Local Application State

The application currently stores data locally on each production instance. ALB
sticky sessions keep a user on one target, but this is not shared or highly
available storage. The next architectural improvement is a managed shared
database and centralized session storage.

## Future Improvements

- Use remote encrypted Terraform state with locking.
- Replace long-lived AWS keys with IAM roles or short-lived credentials.
- Add HTTPS with ACM and Route 53.
- Store application data in RDS or DynamoDB.
- Store sessions in Redis or another shared session backend.
- Add rolling deployment and automated rollback.
- Publish test reports and deployment metadata in Jenkins.
- Add CloudWatch metrics, logs, alarms, and cost controls.
- Provision a custom VPC with private production subnets and managed egress.

## Cost Cleanup

The environment is designed to be created on demand. After a demonstration:

    cd infra/cicd/terraform
    terraform destroy

Review the destroy plan before approval, then confirm that the EC2 instances,
ALB, target group, and project security groups were removed.
