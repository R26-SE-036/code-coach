public class GenWhileNoUpdateFix120 {
    static int gather(int attempts, int count) {
        int sum = 0;
        while (attempts < count) {
            sum += attempts;
            attempts++;
        }
        return sum;
    }
}
