public class GenWhileNoUpdateBug147 {
    static int gather(int points, int level) {
        int sum = 0;
        while (points < level) {
            sum += points;
        }
        return sum;
    }
}
