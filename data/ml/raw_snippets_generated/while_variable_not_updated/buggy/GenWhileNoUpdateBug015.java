public class GenWhileNoUpdateBug015 {
    static int gather(int level, int points) {
        int sum = 0;
        while (level < points) {
            sum += level;
        }
        return sum;
    }
}
