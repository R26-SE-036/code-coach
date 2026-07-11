public class GenWhileNoUpdateFix100 {
    static int gather(int points, int stock) {
        int sum = 0;
        while (points < stock) {
            sum += points;
            points++;
        }
        return sum;
    }
}
