public class GenWhileNoUpdateFix091 {
    static int gather(int level, int stock) {
        int sum = 0;
        while (level < stock) {
            sum += level;
            level++;
        }
        return sum;
    }
}
