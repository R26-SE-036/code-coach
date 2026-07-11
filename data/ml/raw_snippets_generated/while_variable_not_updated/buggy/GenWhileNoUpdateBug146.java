public class GenWhileNoUpdateBug146 {
    static int gather(int stock, int budget) {
        int sum = 0;
        while (stock < budget) {
            sum += stock;
        }
        return sum;
    }
}
