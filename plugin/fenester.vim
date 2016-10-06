if !has('python')
    call confirm("Fenester needs Python to work")
    finish
endif


let s:path = fnamemodify(resolve(expand('<sfile>:p')), ':h')

let s:fenester_py = s:path . '/fenester.py'

command! FenArrange exe 'pyf ' s:fenester_py
