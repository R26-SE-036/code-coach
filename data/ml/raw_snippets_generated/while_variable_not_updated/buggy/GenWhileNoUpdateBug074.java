public class GenWhileNoUpdateBug074 {
    static int gather(int quota, int attempts) {
        int sum = 0;
        while (quota < attempts) {
            sum += quota;
        }
        return sum;
    }
}
