public class GenWhileNoUpdateBug120 {
    static int gather(int attempts, int count) {
        int sum = 0;
        while (attempts < count) {
            sum += attempts;
        }
        return sum;
    }
}
