import jenkins.model.Jenkins
import hudson.model.User
import hudson.plugins.git.GitSCM
import hudson.security.FullControlOnceLoggedInAuthorizationStrategy
import hudson.security.HudsonPrivateSecurityRealm
import hudson.util.Secret
import hudson.plugins.git.BranchSpec
import hudson.plugins.git.UserRemoteConfig
import com.cloudbees.plugins.credentials.CredentialsScope
import com.cloudbees.plugins.credentials.SystemCredentialsProvider
import com.cloudbees.plugins.credentials.domains.Domain
import org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl
import org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition
import org.jenkinsci.plugins.workflow.job.WorkflowJob


def jenkins = Jenkins.get()

def adminUsername = System.getenv("JENKINS_ADMIN_USER")
def adminPassword = System.getenv("JENKINS_ADMIN_PASSWORD")
def applicationSecret = System.getenv("DMS_SECRET_KEY")

if (!adminUsername || !adminPassword || !applicationSecret) {
    throw new IllegalStateException(
        "Required Jenkins environment variables are missing"
    )
}


// Configure Jenkins security.
def securityRealm = jenkins.getSecurityRealm()

if (!(securityRealm instanceof HudsonPrivateSecurityRealm)) {
    securityRealm = new HudsonPrivateSecurityRealm(false)
    jenkins.setSecurityRealm(securityRealm)
}

if (User.getById(adminUsername, false) == null) {
    securityRealm.createAccount(adminUsername, adminPassword)
}

def authorizationStrategy =
    new FullControlOnceLoggedInAuthorizationStrategy()

authorizationStrategy.setAllowAnonymousRead(false)
jenkins.setAuthorizationStrategy(authorizationStrategy)


// Configure the built-in node.
jenkins.setNumExecutors(1)
jenkins.setLabelString("docker")


// Create the application secret credential.
def credentialsProvider = SystemCredentialsProvider.getInstance()

def existingCredential = credentialsProvider.credentials.find {
    it.id == "dms-secret-key"
}

if (existingCredential == null) {
    def credential = new StringCredentialsImpl(
        CredentialsScope.GLOBAL,
        "dms-secret-key",
        "Secret key for the domain monitoring application",
        Secret.fromString(applicationSecret)
    )

    credentialsProvider.store.addCredentials(
        Domain.global(),
        credential
    )
}


// Configure the GitHub repository.
def repositoryUrl =
    "https://github.com/OranAmarDevops/DevopsTMP.git"

def scm = new GitSCM(
    [
        new UserRemoteConfig(
            repositoryUrl,
            null,
            null,
            null
        )
    ],
    [
        new BranchSpec("*/main")
    ],
    null,
    null,
    []
)


// Create or update the Pipeline job.
def jobName = "domain-monitoring-ci"

def pipelineJob = jenkins.getItem(jobName)

if (pipelineJob == null) {
    pipelineJob = jenkins.createProject(
        WorkflowJob.class,
        jobName
    )
}

def pipelineDefinition = new CpsScmFlowDefinition(
    scm,
    "domain-monitoring-system/Jenkins/Jenkinsfile.ci"
)

pipelineDefinition.setLightweight(true)

pipelineJob.setDefinition(pipelineDefinition)
pipelineJob.save()

jenkins.save()

println("Jenkins automatic configuration completed")