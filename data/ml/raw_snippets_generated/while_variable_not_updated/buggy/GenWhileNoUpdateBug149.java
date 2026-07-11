public class GenWhileNoUpdateBug149 {
    static int gather(int points, int budget) {
        int sum = 0;
        while (points < budget) {
            sum += points;
        }
        return sum;
    }
}
