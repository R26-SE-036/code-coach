public class GenWhileNoUpdateBug166 {
    static int gather(int steps, int budget) {
        int sum = 0;
        while (steps < budget) {
            sum += steps;
        }
        return sum;
    }
}
