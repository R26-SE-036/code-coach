public class GenWhileNoUpdateFix087 {
    static int gather(int count, int level) {
        int sum = 0;
        while (count < level) {
            sum += count;
            count++;
        }
        return sum;
    }
}
