public class GenWhileNoUpdateBug167 {
    static int gather(int total, int stock) {
        int sum = 0;
        while (total < stock) {
            sum += total;
        }
        return sum;
    }
}
