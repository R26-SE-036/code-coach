public class GenWhileNoUpdateBug006 {
    static int gather(int level, int steps) {
        int sum = 0;
        while (level < steps) {
            sum += level;
        }
        return sum;
    }
}
