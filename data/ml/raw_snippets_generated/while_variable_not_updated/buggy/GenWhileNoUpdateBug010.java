public class GenWhileNoUpdateBug010 {
    static int gather(int level, int total) {
        int sum = 0;
        while (level < total) {
            sum += level;
        }
        return sum;
    }
}
