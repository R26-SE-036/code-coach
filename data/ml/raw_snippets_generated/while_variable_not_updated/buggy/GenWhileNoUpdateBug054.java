public class GenWhileNoUpdateBug054 {
    static int gather(int total, int steps) {
        int sum = 0;
        while (total < steps) {
            sum += total;
        }
        return sum;
    }
}
