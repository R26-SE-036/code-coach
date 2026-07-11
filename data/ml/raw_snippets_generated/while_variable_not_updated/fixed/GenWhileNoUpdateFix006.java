public class GenWhileNoUpdateFix006 {
    static int gather(int level, int steps) {
        int sum = 0;
        while (level < steps) {
            sum += level;
            level++;
        }
        return sum;
    }
}
