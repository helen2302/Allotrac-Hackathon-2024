let employId=document.querySelector("#InputId");
let password=document.querySelector("#InputPassword");
let form=document.querySelector("form");

function showError(input,message){
  let parent=input.parentElement;
  let small=parent.querySelector("small");
  parent.classList.add('error');
  small.innerText=message;
}
function showSuccess(input){
  let parent=input.parentElement;
  let small=parent.querySelector("small");
  parent.classList.remove('error');
  small.innerText='';
}

function checkEmptyError(ListInput){
  ListInput.forEach(input => {
    input.value=input.value.trim();
    let mess='';
    if(input==employId){
      mess='Employee ID';
    }else if(input==password){
      mess='Password'
    }
    if(!input.value){
      showError(input,'Please enter your '+mess)
    }else{
      showSuccess(input)
    }
  });
}

function checkLengthError(input,inputlength){
  input.value=input.value.trim();
  
  if(input.value.lenth!=inputlength){
    showError(input,"Wrong Employee ID")
    return true
  }
  showSuccess(input)
  return false
}

form.addEventListener('submit',function(e){
  e.preventDefault()
  let isEmptyError=checkEmptyError([employId,password])
  let isEmployeeLengthError=checkLengthError(employId,10);
  if(isEmptyError || isEmployeeLengthError){

  }
  else{
    ///logic,call API
  }
})