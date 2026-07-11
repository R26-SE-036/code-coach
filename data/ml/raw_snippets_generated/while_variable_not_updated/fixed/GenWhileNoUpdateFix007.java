public class GenWhileNoUpdateFix007 {
    static int gather(int attempts, int total) {
        int sum = 0;
        while (attempts < total) {
            sum += attempts;
            attempts++;
        }
        return sum;
    }
}
