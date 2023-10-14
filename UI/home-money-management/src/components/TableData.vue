<template>
    <p>
        HERE WILL BE THE TABLE WITH DATA
    </p>
</template>

<style scoped></style>

<script lang="ts">
import { defineComponent } from 'vue';
interface Transaction {
    id: number;
    transaction_type: string,
    category: string,
    date: string,
    title: string,
    total: number,
    owner_id: number,
    account_id: number,
}
export default defineComponent({
    name: 'TableData',
    props: {
        transactions: {
            type: Array as () => Transaction[],
            required: true
        }
    },
});
</script>