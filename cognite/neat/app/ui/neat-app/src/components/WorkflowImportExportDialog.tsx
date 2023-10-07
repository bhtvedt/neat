import Button from "@mui/material/Button"
import Dialog from "@mui/material/Dialog"
import DialogActions from "@mui/material/DialogActions"
import DialogContent from "@mui/material/DialogContent"
import DialogTitle from "@mui/material/DialogTitle"
import React from "react"
import { useEffect, useState } from "react"
import { WorkflowDefinition } from "types/WorkflowTypes"
import CdfPublisher from "./CdfPublisher"
import CdfDownloader from "./CdfDownloader"
import LocalUploader from "./LocalUploader"
import { getNeatApiRootUrl, getSelectedWorkflowName } from "./Utils"


export default function WorkflowImportExportDialog(props: any)
{
    const neatApiRootUrl = getNeatApiRootUrl();
    const [dialogOpen, setDialogOpen] = useState(false);
    const [component, setComponent] = useState<WorkflowDefinition>(null);
    const handleDialogCancel = () => {
        setDialogOpen(false);
    };

    const onDownloadSuccess = (fileName: string, hash: string) => {
        console.log("onDownloadSuccess", fileName, hash)
        props.onDownloaded(fileName, hash);
        setDialogOpen(false);
    }
    const packageWorkflow = () => {
        const url = neatApiRootUrl + "/api/workflow/package/" + getSelectedWorkflowName();
        fetch(url, {
          method: "post", headers: {
            'Content-Type': 'application/json;charset=utf-8'
          }
        }).then((response) => response.json()).then((data) => {
           const downloadUrl = neatApiRootUrl+"/data/workflows/"+data.package+"?version="+data.hash;
           const link = document.createElement("a");
           link.download = "package.zip";
           link.href = downloadUrl;
           document.body.appendChild(link);
           link.click();
           document.body.removeChild(link);

        }).catch((error) => {
          console.error('Error:', error);
        })
      }

return (
<React.Fragment >
<Button variant="outlined" onClick={(event)=>{setDialogOpen(true)}} sx={{ marginTop: 2, marginRight: 1 }} >Import/Export</Button>

<Dialog open={dialogOpen} onClose={handleDialogCancel}>
<DialogTitle>Workflow Import/Export</DialogTitle>
<DialogContent>
    <CdfPublisher type="workflow" />
    <CdfDownloader type="workflow-package" onDownloadSuccess={onDownloadSuccess} />
    <LocalUploader fileType="workflow" action="install" stepId="none" workflowName={getSelectedWorkflowName()} onUpload={onDownloadSuccess} />
    <Button variant="outlined" onClick={packageWorkflow} sx={{ marginTop: 2, marginRight: 1 }} >Download from NEAT</Button>
</DialogContent>
<DialogActions>
  <Button variant="outlined" size="small" onClick={handleDialogCancel}>Cancel</Button>
</DialogActions>
</Dialog>
</React.Fragment>
)
}