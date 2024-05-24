function insertTextAtSelection(div, txt) {
    //get selection area so we can position insert
    let sel = window.getSelection();
    let text = div.textContent;
    let before = Math.min(sel.focusOffset, sel.anchorOffset);
    let after = Math.max(sel.focusOffset, sel.anchorOffset);
    //ensure string ends with \n so it displays properly
    let afterStr = text.substring(after);
    if (afterStr == "") afterStr = "\n";
    //insert content
    div.textContent = text.substring(0, before) + txt + afterStr;
    //restore cursor at correct position
    sel.removeAllRanges();
    let range = document.createRange();
    //childNodes[0] should be all the text
    range.setStart(div.childNodes[0], before + txt.length);
    range.setEnd(div.childNodes[0], before + txt.length);
    sel.addRange(range);
}

export function forcePlain(node) {
    const enter = e => {
        //override pressing enter in contenteditable
        if (e.keyCode == 13)
        {
            //don't automatically put in divs
            e.preventDefault();
            e.stopPropagation();
            //insert newline
        }
    }

    const paste = e => {
        //cancel paste
        e.preventDefault();
        //get plaintext from clipboard
        let text = (e.originalEvent || e).clipboardData.getData('text/plain');
        //insert text manually
        insertTextAtSelection(node, text);
    }
    node.addEventListener("paste", paste);
    node.addEventListener("keydown", enter);

    return () => {
        node.removeEventListener("paste", cb)
        node.removeEventListener("keydown", enter)
    };
}