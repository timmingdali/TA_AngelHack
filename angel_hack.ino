#define red 10
#define yellow 11

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  pinMode(red,INPUT);
  pinMode(yellow,INPUT);

}

void loop() {
  // put your main code here, to run repeatedly:
  if(digitalRead(red)==HIGH){
    Serial.println("red");
  }
  else if(digitalRead(yellow)==HIGH){
    Serial.println("yellow");
  }else{
    Serial.println("waiting");
  }
  while(true){
    char u=Serial.read();
    if(u=='f'){
      break;
    }
  }
}
