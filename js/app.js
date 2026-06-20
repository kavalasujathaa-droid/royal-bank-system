console.log("ROYAL BANK JS LOADED");

async function handleLogin() {

    const username =
        document.getElementById("login-username").value;

    const password =
        document.getElementById("login-password").value;

    try {

        const response = await fetch(
            "http://127.0.0.1:5000/login",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            }
        );

        const data = await response.json();

        if (data.success) {
            if (data.success) {

    localStorage.setItem(
        "bank_user",
        username
    );

    alert("Login Successful");

    window.location.href =
    "dashboard.html";

}

            alert("Login Successful");

        } else {

            alert(data.message);

        }

    } catch (error) {

        console.error(error);
        alert("Server Connection Failed");

    }
}
async function handleRegister(){

    const fullName =
    document.getElementById(
        "reg-name"
    ).value;

    const username =
    document.getElementById(
        "reg-username"
    ).value;

    const password =
    document.getElementById(
        "reg-password"
    ).value;

    try{

        const response =
        await fetch(
            "http://127.0.0.1:5000/register",
            {
                method:"POST",
                headers:{
                    "Content-Type":"application/json"
                },
                body:JSON.stringify({
                    full_name:fullName,
                    username:username,
                    password:password
                })
            }
        );

        const data =
        await response.json();

        alert(data.message);

    }catch(err){

        console.error(err);
        alert("Registration Failed");

    }
}

function handleAdmin(){

    window.location.href =
    "admin.html";

}