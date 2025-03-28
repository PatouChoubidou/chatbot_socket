<script setup>
import { defineModel, defineProps } from 'vue'

defineProps({
  label: String
})

const autoPlayLLMAnswer = defineModel({type: Boolean, default: false})

const toggleVal = (e) => { 
    console.log("swith toggle")
    autoPlayLLMAnswer.value = autoPlayLLMAnswer.value ? false : true
}

</script>

<template>
    <div class="toggle__wrapper" >
        <div class="toggle_bg" @click="toggleVal" :class="{ active: autoPlayLLMAnswer }">
          <button></button>
        </div>
        <label>{{label}}</label>
    </div>
</template>

<style scoped>

button {
    height: 25px;
    width: 25px;
    border-radius: 50%;
    background-color: rgb(255, 255, 255);
    border: solid 2px grey;
}

.toggle_bg{
  display: flex;
  flex-direction: row;
  width: 45px;
  height: 22px;
  background-color: lightgrey;
  
  border-radius: 25px;
  align-items: center;
  justify-content: flex-start;
  box-shadow: inset 1px 1px 1px 1px rgb(186, 186, 186);
}

.toggle_bg.active{
  justify-content: flex-end;
}

.toggle_bg.active button{
  background-color: aquamarine;
}

.toggle__wrapper{
    display: flex;
    flex-direction: row;
    gap: 15px;
    padding: 5px 0;
    flex-direction: row-reverse
}

@media (min-width: 1024px) {
  
}
</style>
