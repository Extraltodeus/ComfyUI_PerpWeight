import torch


class CLIPTextEncodePerpWeight:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"text": ("STRING", {"multiline": True}),
                             "clip": ("CLIP", ),
                             }}
    RETURN_TYPES = ("CONDITIONING",)
    FUNCTION = "encode"

    CATEGORY = "conditioning"

    def encode(self, clip, text):
        empty_tokens = clip.tokenize("")

        sdxl_flag = isinstance(empty_tokens, dict)
        
        if sdxl_flag:
            empty_cond, empty_cond_pooled = clip.encode_from_tokens(empty_tokens, return_pooled=True)
            tokens = clip.tokenize(text)
            unweighted_tokens = {}
            unweighted_tokens["l"] = [[(t, 1.0) for t,_ in x] for x in tokens["l"]]
            unweighted_tokens["g"] = [[(t, 1.0) for t,_ in x] for x in tokens["g"]]
            unweighted_cond, unweighted_pooled = clip.encode_from_tokens(unweighted_tokens, return_pooled=True)

            cond = torch.clone(unweighted_cond)
            for i in range(unweighted_cond.shape[0]):
                for j in range(unweighted_cond.shape[1]):
                    weight_l = tokens["l"][(j//77)][(j%77)][1]
                    if weight_l != 1.0:
                        token_vector_l = unweighted_cond[i][j][:768]
                        zero_vector_l = empty_cond[0][(j%77)][:768]
                        perp_l = ((torch.mul(zero_vector_l, token_vector_l).sum())/(torch.norm(token_vector_l)**2)) * token_vector_l
                        if weight_l > 1.0:
                            cond[i][j][:768] = token_vector_l + (weight_l * perp_l)
                        elif (weight_l > 0.0) and (weight_l < 1.0):
                            cond[i][j][:768] = token_vector_l - ((1 - weight_l) * perp_l)
                        elif weight_l < 0.0:
                            cond[i][j][:768] = token_vector_l + (weight_l * perp_l)
                        elif weight_l == 0.0:
                            cond[i][j][:768] = empty_cond[0][(j%77)][:768]
                    
                    weight_g = tokens["g"][(j//77)][(j%77)][1]
                    if weight_g != 1.0:
                        token_vector_g = unweighted_cond[i][j][768:]
                        zero_vector_g = empty_cond[0][(j%77)][768:]
                        perp_g = ((torch.mul(zero_vector_g, token_vector_g).sum())/(torch.norm(token_vector_g)**2)) * token_vector_g
                        if weight_g > 1.0:
                            cond[i][j][768:] = token_vector_g + (weight_g * perp_g)
                        elif (weight_g > 0.0) and (weight_g < 1.0):
                            cond[i][j][768:] = token_vector_g - ((1 - weight_g) * perp_g)
                        elif (weight_g < 0.0):
                            cond[i][j][768:] = token_vector_g + (weight_g * perp_g)
                        elif weight_g == 0.0:
                            cond[i][j][768:] = empty_cond[0][(j%77)][768:]
        else:
            empty_cond, empty_cond_pooled = clip.encode_from_tokens(empty_tokens, return_pooled=True)
            tokens = clip.tokenize(text)
            unweighted_tokens = [[(t, 1.0) for t,_ in x] for x in tokens]
            unweighted_cond, unweighted_pooled = clip.encode_from_tokens(unweighted_tokens, return_pooled=True)

            cond = torch.clone(unweighted_cond)
            for i in range(unweighted_cond.shape[0]):
                for j in range(unweighted_cond.shape[1]):
                    weight = tokens[(j//77)][(j%77)][1]
                    if weight != 1.0:
                        token_vector = unweighted_cond[i][j]
                        zero_vector = empty_cond[0][(j%77)]
                        perp = ((torch.mul(zero_vector, token_vector).sum())/(torch.norm(token_vector)**2)) * token_vector
                        if weight > 1.0:
                            cond[i][j] = token_vector + (weight * perp)
                        elif (weight > 0.0) and (weight < 1.0):
                            cond[i][j] = token_vector - ((1 - weight) * perp)
                        elif (weight < 0.0):
                            cond[i][j] = token_vector + (weight * perp)
                        elif weight == 0.0:
                            cond[i][j] = empty_cond[0][(j%77)]
        
        return ([[cond, {"pooled_output": unweighted_pooled}]], )


NODE_CLASS_MAPPINGS = {
    "CLIPTextEncodePerpWeight": CLIPTextEncodePerpWeight,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CLIPTextEncodePerpWeight": "CLIP Text Encode (Perp-Weight)",
}
