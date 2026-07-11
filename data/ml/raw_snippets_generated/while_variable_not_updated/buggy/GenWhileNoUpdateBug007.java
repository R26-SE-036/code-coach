public class GenWhileNoUpdateBug007 {
    static int gather(int attempts, int total) {
        int sum = 0;
        while (attempts < total) {
            sum += attempts;
        }
        return sum;
    }
}
