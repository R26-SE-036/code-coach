public class GenWhileNoUpdateBug095 {
    static int gather(int stock, int budget) {
        int sum = 0;
        while (stock < budget) {
            sum += stock;
        }
        return sum;
    }
}
