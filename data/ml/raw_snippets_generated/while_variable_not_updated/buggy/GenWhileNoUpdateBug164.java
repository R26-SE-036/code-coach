public class GenWhileNoUpdateBug164 {
    static int gather(int total, int attempts) {
        int sum = 0;
        while (total < attempts) {
            sum += total;
        }
        return sum;
    }
}
