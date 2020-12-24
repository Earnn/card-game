import models
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI,Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models import Customer,GlobalGameState,CustomerGameState
from schemas import CustomerSchema,GlobalGameStateSchema
from db import SessionLocal, engine
from config import settings
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class NewGameRequest(BaseModel):
    customer_id: int
    my_best:int = 0

class CardOpenRequest(BaseModel):
    customer_id: int
    card_no:int
    prev_card_no:int

class CardOpenResponse:
    def __init__(self,
    customer_game_state: str,
    my_best: int,
    global_best:int,
    isEndGame:bool=False
    ):

        self.customer_game_state = customer_game_state
        self.my_best = my_best
        self.global_best = global_best

class NewGameResponse:
    def __init__(self,
    customer_name: str,
    customer_game_state: str,
    my_best: int,
    global_best:int ):

        self.customer_name = customer_name
        self.customer_game_state = customer_game_state
        self.my_best = my_best
        self.global_best = global_best

class GameResponse:
    def __init__(self, state: str, global_best: int ):
        self.state = state
        self.global_best = global_best

class NewCustomerResponse:
    def __init__(self, state: str, global_best: int ):
        self.state = state
        self.global_best = global_best

class CustomerResponse:
    def __init__(self, first_name: str, last_name: str,phone_number : str ):
        self.first_name = first_name
        self.last_name = last_name
        self.phone_number = phone_number


@app.get("/customers")
async def get_customers(db: Session = Depends(get_db)):
    customers = db.query(Customer).all()
    response = CustomerResponse(
        first_name=customers[0].first_name,
        last_name=customers[0].last_name,
        phone_number=customers[0].phone_number
    )
    return JSONResponse(status_code=200,
    content=jsonable_encoder({
        "status": {"code": 1000,"header":"","description":"Success"},
        "data":jsonable_encoder(response)})
        )

@app.post("/customer")
async def create_new_customer(customer_request: CustomerSchema, db: Session = Depends(get_db)):

    customer = Customer()
    customer.first_name = customer_request.first_name
    customer.last_name = customer_request.last_name
    customer.phone_number = customer_request.phone_number

    db.add(customer)
    db.commit()
    
    return JSONResponse(status_code=200,
    content=jsonable_encoder({
        "status": {"code": 1000,"header":"","description":"Success"},
        "data":jsonable_encoder(customer_request)})
        )

@app.post("/game/global-game")
async def create_new_global_game(global_game_request: GlobalGameStateSchema, db: Session = Depends(get_db)):

    global_game_state = GlobalGameState()
    global_game_state.state = global_game_request.state
    global_game_state.global_best = global_game_request.global_best

    db.add(global_game_state)
    db.commit()

    return JSONResponse(status_code=200,
    content=jsonable_encoder({
        "status": {"code": 1000,"header":"","description":"Success"},
        "data":jsonable_encoder(global_game_request)})
    )


@app.post("/game/new-game")
async def new_game(new_game_request: NewGameRequest,db: Session = Depends(get_db)):

    customer = db.query(Customer).filter(Customer.id == new_game_request.customer_id).first()
    db.commit()
 
    # Verify whether user is valid or not.
    if customer is None :
        # if not valid then can't play a game.
        return JSONResponse(status_code=200,content=jsonable_encoder({
        "status": {"code":1999,"header":"","description":"Fail. Customer does not exist."},
        "data":{}})
        )

    # Retrive the game from database.
    game = get_game()
    c_game_state_obj = db.query(CustomerGameState).filter(CustomerGameState.customer_id == new_game_request.customer_id).first()

    if c_game_state_obj is None :
        # Create customer game state and insert to database
        c_game_state = CustomerGameState()
        c_game_state.current_state = settings.default_card_set
        c_game_state.my_best = 0
        c_game_state.customer_id = new_game_request.customer_id
        db.add(c_game_state)
        db.commit()
        
    else:
        # Reset game
        update_customer_game_state(
            c_game_state_obj.customer_id,
            settings.default_card_set,
            0
            )
    

    response  = NewGameResponse(
        customer_name=customer.first_name,
        customer_game_state=settings.default_card_set,
        my_best=0,
        global_best=game.global_best
    )

    return JSONResponse(status_code=200,
    content=jsonable_encoder({
        "status": {"code": 1000,"header":"","description":"Success"},
        "data":jsonable_encoder(response)})
        )

@app.post("/game/card-open")
async def open_card(request:CardOpenRequest, db: Session = Depends(get_db)):

    # Validate card no that user selected
    if not validate_card_no(request.card_no):
        return JSONResponse(status_code=200,content=jsonable_encoder({
        "status": {"code":1999,"header":"","description":"Fail. Card no is not valid."},
        "data":{}})
        )

    customer_game = db.query(CustomerGameState).filter(CustomerGameState.customer_id == request.customer_id)
    customer_game_obj = customer_game.first()
    if customer_game_obj is None:
        return JSONResponse(status_code=200,content=jsonable_encoder({
        "status": {"code":1999,"header":"","description":"Fail. User does not exist."},
        "data":{}})
        )

    game = get_game()

    game_state_arr = game.state.split(",")
    customer_state_arr= customer_game_obj.current_state.split(",")
    
    # Use for return to Frontend
    customer_current_state=""
    my_best= customer_game_obj.my_best
    my_best+=1
    # Validate opened card.
    counter = customer_game_obj.current_state.count('x')
    if counter == 1:
        # last card to go
        customer_state_arr[request.card_no]=game_state_arr[request.card_no]
        customer_current_state = ','.join(customer_state_arr)
        # check whether these two cards match
        prev_card = game_state_arr[request.prev_card_no]
        curr_care = game_state_arr[request.card_no]

        if (prev_card == curr_care):
            update_customer_game_state(request.customer_id,customer_current_state,my_best)
        
        if game.global_best == 0 or my_best < game.global_best:
            update_global_game(settings.version_game_id,my_best)
            
            # end game
        response  = CardOpenResponse(
                customer_game_state=customer_current_state,
                my_best=my_best,
                global_best=game.global_best,
                isEndGame=True
        )

        return JSONResponse(status_code=200,
        content=jsonable_encoder({
            "status": {"code": 1000,"header":"","description":"Success"},
            "data":jsonable_encoder(response)})
            )

    elif counter % 2 == 1:
        # Validate previous card number.
        if not validate_card_no(request.prev_card_no):
            return JSONResponse(status_code=200,content=jsonable_encoder({
            "status": {"code":1999,"header":"","description":"Fail. Card no is not valid."},
            "data":{}})
            )
        
        customer_state_arr[request.card_no]=game_state_arr[request.card_no]
        customer_current_state = ','.join(customer_state_arr)
        # check whether these two cards match
        prev_card = game_state_arr[request.prev_card_no]
        curr_care = game_state_arr[request.card_no]

        if (prev_card == curr_care):
            update_customer_game_state(request.customer_id,customer_current_state,my_best)
        else:
            # close current card & previous card.
            customer_state_arr[request.prev_card_no]="x"
            customer_state_arr[request.card_no]="x"

            # Update customer game state
            temp = ','.join(customer_state_arr)
            update_customer_game_state(request.customer_id,temp,my_best)

    elif counter %2 == 0:
        # one to go for check if card match, then can update the current state right away
        customer_state_arr[request.card_no]=game_state_arr[request.card_no]

        # Update customer game state
        customer_current_state = ','.join(customer_state_arr)
        update_customer_game_state(request.customer_id,customer_current_state,my_best)
        
    
    response  = CardOpenResponse(
        customer_game_state=customer_current_state,
        my_best=my_best,
        global_best=game.global_best,
        isEndGame=False
    )

    return JSONResponse(status_code=200,
    content=jsonable_encoder({
        "status": {"code": 1000,"header":"","description":"Success"},
        "data":jsonable_encoder(response)})
        )

def validate_card_no(card_no):
    if card_no <0 or card_no >11:
        return False
    return True

def update_global_game(game_version_id,global_best):
    db = SessionLocal()
    global_game_state = db.query(GlobalGameState).filter(GlobalGameState.id == game_version_id)
    global_game_state.update({GlobalGameState.global_best:global_best})
    db.commit()

def update_customer_game_state(customer_id,current_state,my_best):
    db = SessionLocal()
    customer_game = db.query(CustomerGameState).filter(CustomerGameState.customer_id == customer_id)
    customer_game.update({
        CustomerGameState.current_state: current_state,
        CustomerGameState.my_best:my_best
    },synchronize_session='fetch')
    db.commit()


def get_game():
    # Get game from database
    db = SessionLocal()
    global_game_state = db.query(GlobalGameState).filter(GlobalGameState.id == settings.version_game_id).first()
    db.commit()

    # Create game object
    response = GameResponse(state=global_game_state.state,global_best=global_game_state.global_best)
    return response
