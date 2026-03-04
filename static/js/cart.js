function getToken(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
         const cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
    if (cookie.substring(0, name.length + 1) === (name + '=')) {
         cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
             break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getToken('csrftoken');

function getCookie(name) {
		    // Split cookie string and get all individual name=value pairs in an array
		    let cookieArr = document.cookie.split(";");

		    // Loop through the array elements
		    for(let i = 0; i < cookieArr.length; i++) {
		        const cookiePair = cookieArr[i].split("=");

		        /* Removing whitespace at the beginning of the cookie name
		        and compare it with the given string */
		        if(name == cookiePair[0].trim()) {
		            // Decode the cookie value and return
		            return decodeURIComponent(cookiePair[1]);
		        }
		    }

		    // Return null if not found
		    return null;
		}

		let cart = JSON.parse(getCookie('cart')) ||{}
      
		if (cart == undefined){
			cart = {}
			console.log('Cart Created!', cart)
			document.cookie ='cart=' + JSON.stringify(cart) + ";domain=;path=/"
		}
		console.log('Cart:', cart)


const updatebtns = document.getElementsByClassName('update-cart')


for(let i = 0; i < updatebtns.length; i++){
    updatebtns[i].addEventListener('click', function(){
        const productId = this.dataset.product
        const action = this.dataset.action
        console.log('productId', productId, 'action:', action)

        console.log('USER', user)
        if(user === 'AnonymousUser'){
            addCookieItem(productId, action)
		}else{
			updateUserOrder(productId, action)
        }
    })
}

function addCookieItem(productId, action){
	console.log('User is not authenticated')

	if (action == 'add'){
		if (cart[productId] == undefined){
		cart[productId] = {'quantity':1}

		}else{
			cart[productId]['quantity'] += 1
		}
	}

	if (action == 'remove'){
		cart[productId]['quantity'] -= 1

		if (cart[productId]['quantity'] <= 0){
			console.log('Item should be deleted')
			delete cart[productId];
		}
	}
	console.log('CART:', cart)
	document.cookie ='cart=' + JSON.stringify(cart) + ";domain=;path=/"

    setTimeout(() => {
        location.reload();
    }, 100);
}

function updateUserOrder(productId, action){
    console.log('User is lgged in, sending data....')

    const url = '/update_item/'

    fetch(url,{
        method: 'POST',
        headers : {
            'Content-Type': 'application/json',
            'X-CSRFToken':csrftoken,
        },
        body:JSON.stringify({
            'productId': productId, 'action': action
        })
    })

    .then((response) =>{
        return response.json()
    })

    .then((data) => {
        console.log('data:', data);
        document.getElementById('cart-total').innerText = data.cartItems;
      
    })
    
    setTimeout(() => {
        location.reload();
    }, 100);
    
}

