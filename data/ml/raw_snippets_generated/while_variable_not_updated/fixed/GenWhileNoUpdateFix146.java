public class GenWhileNoUpdateFix146 {
    static int gather(int stock, int budget) {
        int sum = 0;
        while (stock < budget) {
            sum += stock;
            stock++;
        }
        return sum;
    }
}
