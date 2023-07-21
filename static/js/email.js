function addTagToEmailTitle(tag){
    document.getElementById("subject").value += tag;
}

function addTagToEmailBody(tag){
    console.log(tag)
    data = CKEDITOR.instances['id_content'].getData();
    CKEDITOR.instances['id_content'].setData(data + tag);
}

function showTags(){

    tags = document.getElementById("tags-container")
    if (tags.hidden)
    {
        document.querySelector('#hidden-cc-groups').innerHTML = '';
        document.querySelector('#hidden-cc-contacts').innerHTML = '';
        document.querySelector('#cc-container').style.display = 'none';

        tags.hidden = false;
    }
    else
    {
        document.querySelector('#cc-container').style.display = 'block';
        tags.hidden = true;
    }

}