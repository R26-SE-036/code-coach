public class GenWhileNoUpdateBug035 {
    static int gather(int steps, int points) {
        int sum = 0;
        while (steps < points) {
            sum += steps;
        }
        return sum;
    }
}
